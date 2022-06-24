import os
from flask import Flask, request, abort, jsonify
from flask_cors import CORS

from models import setup_db, Book

BOOKS_PER_SHELF = 8

def paginate_books(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * BOOKS_PER_SHELF
    end = start + BOOKS_PER_SHELF

    books = [book.format() for book in selection]
    current_books = books[start:end]

    return current_books

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    # Retrieve all books
    @app.route('/books', methods=['GET'])
    def get_books():
        try:
            books = Book.query.all()
            current_books = paginate_books(request, books)
            if len(current_books) == 0:
                abort(404)
            return jsonify({
                'success': True,
                'books': current_books,
                'total_books': len(books)
            })
        except Exception:
            abort(404)

    # Update a book's rating
    @app.route('/books/<int:book_id>', methods=['PATCH'])
    def update_book(book_id):
        try:
            book = Book.query.get(book_id)
            if not book:
                abort(404)
            data = request.get_json()
            if 'rating' in data:
                book.rating = int(data['rating'])
            book.update()
            return jsonify({
                'success': True,
                'id': book.id
            })
        except Exception:
            abort(400)

    # Delete a book
    @app.route('/books/<int:book_id>', methods=['DELETE'])
    def delete_book(book_id):
        try:
            book = Book.query.get(book_id)
            if not book:
                abort(404)
            book.delete()
            books = Book.query.all()
            current_books = paginate_books(request, books)
            return jsonify({
                'success': True,
                'deleted': book_id,
                'books': current_books,
                'total_books': len(books)
            })
        except Exception:
            abort(422)

    # Create a new book
    @app.route('/books', methods=['POST'])
    def create_book():
        try:
            data = request.get_json()
            title = data.get('title', None)
            author = data.get('author', None)
            rating = data.get('rating', None)
            search = data.get('search', None)

            if search:
                books = Book.query.filter(Book.title.ilike('%' + search + '%')).all()
                current_books = paginate_books(request, books)
                return jsonify({
                    'success': True,
                    'books': current_books,
                    'total_books': len(books)
                })

            else:
                book = Book(title=title, author=author, rating=rating)
                book.insert()
                books = Book.query.all()
                current_books = paginate_books(request, books)
                return jsonify({
                    'success': True,
                    'created': book.id,
                    'books': current_books,
                    'total_books': len(books)
                })
                
        except Exception:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405

    return app
