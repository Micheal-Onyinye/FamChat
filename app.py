from APP import define_app, create_database, setup_general_chat, socketio 

app = define_app()


with app.app_context():
        create_database(app)
        setup_general_chat()

if __name__ == '__main__':


        socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
