from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Book, Member, Transaction
from config import Config
from datetime import datetime, date

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Home Route
@app.route('/')
def index():
    return render_template('index.html')

# Book Routes
@app.route('/books')
def list_books():
    books = Book.query.all()
    return render_template('books.html', books=books)

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        quantity = request.form.get('quantity')
        rental_fee = request.form.get('rental_fee')

        new_book = Book(title=title, author=author, quantity=quantity, rental_fee=rental_fee)
        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('list_books'))
    
    return render_template('add_edit_book.html')

@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.quantity = request.form.get('quantity')
        book.rental_fee = request.form.get('rental_fee')
        
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('list_books'))

    return render_template('add_edit_book.html', book=book)

@app.route('/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('list_books'))

@app.route('/books/search', methods=['GET'])
def search_books():
    query = request.args.get('query')
    if query:
        books = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) | (Book.author.ilike(f'%{query}%'))
        ).all()
    else:
        books = Book.query.all()
    return render_template('books.html', books=books, search_query=query)


@app.route('/return_book/<int:transaction_id>', methods=['GET', 'POST'])
def return_book(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if request.method == 'POST':
        return_date = datetime.utcnow()
        transaction.return_date = return_date

        # Calculate fees (example: Rs. 10 per day after 7 days)
        days_held = (return_date - transaction.issue_date).days
        rental_period = 7  # days
        daily_fee = 10.0
        fees = max(0, (days_held - rental_period) * daily_fee)
        
        # Update member's debt
        member = transaction.member
        if member.debt + fees <= 500:
            member.debt += fees
            transaction.fees_charged = fees

            # Update the stock
            book = transaction.book
            book.quantity += 1

            db.session.commit()
            flash(f'Book returned successfully! Fees charged: Rs. {fees}', 'success')
            return redirect(url_for('list_transactions'))
        else:
            flash("Member's debt exceeds the Rs. 500 limit. Cannot return book.", 'danger')
            return redirect(url_for('list_transactions'))

    return render_template('return_book.html', transaction=transaction)


# Member Routes
@app.route('/members')
def list_members():
    members = Member.query.all()
    return render_template('members.html', members=members)

@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        new_member = Member(name=name)
        db.session.add(new_member)
        db.session.commit()
        flash('Member added successfully!', 'success')
        return redirect(url_for('list_members'))
    
    return render_template('add_edit_member.html')

@app.route('/members/edit/<int:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)

    if request.method == 'POST':
        member.name = request.form.get('name')
        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('list_members'))

    return render_template('add_edit_member.html', member=member)

@app.route('/members/delete/<int:member_id>', methods=['POST'])
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted successfully!', 'success')
    return redirect(url_for('list_members'))

# Transaction Routes
@app.route('/transactions')
def list_transactions():
    transactions = Transaction.query.all()
    return render_template('transactions.html', transactions=transactions)

@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    books = Book.query.all()
    members = Member.query.all()
    return render_template('issue_book.html', books=books, members=members, current_date=datetime.utcnow().date())

@app.route('/save_issue_book', methods=['POST'])
def save_issue_book():
    book_id = request.form['book_id']
    member_id = request.form['member_id']
    issue_date = request.form['issue_date']
    due_date = request.form.get('due_date')

    member = Member.query.get(member_id)
    if member.debt > 500:
        flash("Cannot issue book. Member's debt exceeds Rs. 500.", 'danger')
        return redirect(url_for('issue_book'))

    transaction = Transaction(
        book_id=book_id,
        member_id=member_id,
        issue_date=datetime.strptime(issue_date, '%Y-%m-%d'),
        due_date=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None
    )

    book = Book.query.get(book_id)
    if book and book.quantity > 0:
        book.quantity -= 1
        db.session.add(transaction)
        db.session.commit()
        flash('Book issued successfully!', 'success')
    else:
        flash('Book not available for issue.', 'danger')

    return redirect(url_for('list_transactions'))


@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        member_id = request.form.get('member_id')
        new_transaction = Transaction(book_id=book_id, member_id=member_id)
        db.session.add(new_transaction)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('list_transactions'))  # Corrected url_for
    
    # If GET request, render the form
    books = Book.query.all()
    members = Member.query.all()
    return render_template('add_edit_transaction.html', books=books, members=members)

@app.route('/transactions/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if request.method == 'POST':
        transaction.return_date = datetime.utcnow()
        transaction.fees_charged = request.form.get('fees_charged')
        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('list_transactions'))  # Corrected url_for

    return render_template('add_edit_transaction.html', transaction=transaction)

@app.route('/transactions/delete/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('list_transactions'))  # Corrected url_for


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
