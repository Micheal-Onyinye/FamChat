from APP import define_app, create_database

app = define_app()

if __name__ == '__main__':
    create_database(app)
    app.run(debug=True)
