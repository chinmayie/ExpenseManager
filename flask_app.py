from flask import Flask, render_template, redirect, url_for,\
    request, json, session, flash, jsonify
import os
import ssl
from datetime import datetime
from pymongo import MongoClient
app = Flask(__name__)

db = MongoClient(os.environ['MongoClient'],ssl=True,ssl_cert_reqs=ssl.CERT_NONE).exp

@app.route('/', methods=['get','post'])
def index():
    if request.method == 'POST':
        date = datetime.strptime(f"{request.form['date']} {request.form['time']}", '%Y-%m-%d %I:%M %p')
        sub = request.form['sub'] if request.form['sub'] else 0
        d = {
            'id':db.dairy.count_documents({})+1,
            'date': date,
            'in_out': int(request.form['in_out']),
            'cat': int(request.form['main']),
            'sub': int(sub),
            'account': int(request.form['account']),
            'amount': int(request.form['amount']),
            'description': request.form['description'],
            'notes': request.form['notes']
        }
        db.dairy.insert_one(d)
    return(render_template('category.html'))

@app.route('/list/acc/<account_name>')
@app.route('/list/cat/<category_name>')
@app.route('/list')
def list(account_name=None, category_name=None):
    _filter = {'name':account_name} if account_name else {}
    account = {i['id']: i['name'] for i in db.account.find(_filter,{'_id':0})}
    
    _filter_2 = {'name': category_name} if category_name else {} 
    cat = {i['id']: i['name'] for i in db.category.find(_filter_2,{'_id':0, 'id': 1, 'name': 1})}
    if (account_name and not account) or (category_name and not cat):
        return "Items not available"
    _filter_3 = {'account':tuple(account)[0]} if account_name else {}
    _filter_3.update({'cat': tuple(cat)[0]}) if category_name else None
    dairy = db.dairy.find(_filter_3 ,{'_id':0}).sort('date')
    data = {'dairy': dairy, 'account': account, 'cat': cat}
    return(render_template('list.html', data=data))

@app.route('/get_category/<int:typ>')
def cat(typ):
    data = db.category.find({'type':typ},{'_id':0}).sort('pid')
    return jsonify({'data': [i for i in data]})

@app.route('/get_parent_category')
def parent_cat():
    data = db.category.find({'pid':0},{'_id':0}).sort('pid')
    return jsonify({'data': [i for i in data]})

@app.route('/add_category', methods=['POST',"GET"])
def add_category():
    if request.method == 'POST':
        f = dict(request.form)
        dic = {
            'id' : db.category.count_documents({}) + 1,
            'pid' : int(f['pid']),
            'name' : f['name'],
            'type' : int(f['type'])
        } 
        db.category.insert_one(dic)
    return(render_template('add_category.html'))

@app.route('/get_account')
def get_account():
    data = db.account.find({},{'_id':0}).sort('id')
    return {'data': [i for i in data]}


@app.route('/account')
def single_account():
    in_group = db.dairy.aggregate([{"$match": {"in_out":0}},{"$group": {"_id": '$account', "total" : {"$sum": "$amount"}}}])
    income = {i['_id']: i['total'] for i in in_group}
    out_group = db.dairy.aggregate([{"$match": {"in_out":1}},{"$group": {"_id": '$account', "total" : {"$sum": "$amount"}}}])
    outcome = {i['_id']: i['total'] for i in out_group}
    account = {i['id']: i['name'] for i in db.account.find({},{'_id':0})}
    data = {'account': account, 'income': income, 'outcome': outcome} 
    print(data)
    return(render_template('account.html', data=data))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
