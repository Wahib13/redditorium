def initialise_database(session, default_data):
    session.add_all(default_data)
    session.commit()
