user_id = input()
query = "SELECT * FROM users WHERE id = " + user_id
execute(query)
