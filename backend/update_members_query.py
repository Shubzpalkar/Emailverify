import os

# We will read the file and replace the `get_members` query.
filepath = "c:/Users/CW250413/Desktop/tool/Emailverify/backend/routes/members.py"
with open(filepath, "r") as f:
    content = f.read()

old_query = """    query = "SELECT id, email, display_name, role, department, status, last_login, created_at FROM users WHERE workspace_id = ?"
    params = [current_user.workspace_id]"""

new_query = """    query = '''
        SELECT id, email, display_name, role, department, status, last_login, created_at 
        FROM users 
        WHERE workspace_id = ?
        UNION ALL
        SELECT id, email, NULL as display_name, role, department, status, NULL as last_login, created_at 
        FROM invitations 
        WHERE workspace_id = ? AND status = 'Pending'
    '''
    params = [current_user.workspace_id, current_user.workspace_id]"""

content = content.replace(old_query, new_query)

with open(filepath, "w") as f:
    f.write(content)

print("Updated get_members query")
