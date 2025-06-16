from APP import define_app, create_database, setup_general_chat

app = define_app()

if __name__ == '__main__':
    create_database(app)
    with app.app_context():
        setup_general_chat()

    app.run(debug=True)
