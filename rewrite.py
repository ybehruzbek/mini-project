import re

with open('bot/bot.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace view_dhikrs_handler
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("SELECT dhikr_id, title, daily_target, global_target, global_progress FROM Dhikrs WHERE user_id=\?", \(callback\.from_user\.id,\)\)\s*dhikrs = cursor\.fetchall\(\)\s*conn\.close\(\)',
    '''response = supabase.table('dhikrs').select('id, title, daily_target, global_target, global_progress').eq('user_id', callback.from_user.id).execute()
    dhikrs = [(d['id'], d['title'], d['daily_target'], d['global_target'], d['global_progress']) for d in response.data]''',
    code
)

# Replace add_dhikr_process_global
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("INSERT INTO Dhikrs \(user_id, title, daily_target, global_target\) VALUES \(\?, \?, \?, \?\)", \(callback\.from_user\.id, title, daily_tgt, global_tgt\)\)\s*conn\.commit\(\)\s*conn\.close\(\)',
    '''supabase.table('dhikrs').insert({
            'user_id': callback.from_user.id,
            'title': title,
            'daily_target': daily_tgt,
            'global_target': global_tgt,
            'daily_count': 0,
            'global_count': 0,
            'global_progress': 0
        }).execute()''',
    code
)
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("INSERT INTO Dhikrs \(user_id, title, daily_target, global_target\) VALUES \(\?, \?, \?, \?\)", \(message\.from_user\.id, title, daily_tgt, global_tgt\)\)\s*conn\.commit\(\)\s*conn\.close\(\)',
    '''supabase.table('dhikrs').insert({
            'user_id': message.from_user.id,
            'title': title,
            'daily_target': daily_tgt,
            'global_target': global_tgt,
            'daily_count': 0,
            'global_count': 0,
            'global_progress': 0
        }).execute()''',
    code
)

# Replace edit_dhikr_handler
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("SELECT title FROM Dhikrs WHERE dhikr_id=\?", \(dhikr_id,\)\)\s*title = cursor\.fetchone\(\)\[0\]\s*conn\.close\(\)',
    '''response = supabase.table('dhikrs').select('title').eq('id', dhikr_id).execute()
    title = response.data[0]['title']''',
    code
)

# Replace edit_dhikr_process_global
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("UPDATE Dhikrs SET daily_target=\?, global_target=\? WHERE dhikr_id=\?", \(daily_tgt, global_tgt, dhikr_id\)\)\s*conn\.commit\(\)\s*conn\.close\(\)',
    '''supabase.table('dhikrs').update({
            'daily_target': daily_tgt,
            'global_target': global_tgt
        }).eq('id', dhikr_id).execute()''',
    code
)
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("UPDATE Dhikrs SET daily_target=\?, global_target=\? WHERE dhikr_id=\?", \(daily_tgt, global_tgt, dhikr_id\)\)\s*cursor\.execute\("SELECT title FROM Dhikrs WHERE dhikr_id=\?", \(dhikr_id,\)\)\s*title = cursor\.fetchone\(\)\[0\]\s*conn\.commit\(\)',
    '''supabase.table('dhikrs').update({
            'daily_target': daily_tgt,
            'global_target': global_tgt
        }).eq('id', dhikr_id).execute()
    title_resp = supabase.table('dhikrs').select('title').eq('id', dhikr_id).execute()
    title = title_resp.data[0]['title']''',
    code
)

# Replace broadcast_reminder
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("SELECT user_id FROM Users"\)\s*users = cursor\.fetchall\(\)\s*conn\.close\(\)',
    '''response = supabase.table('users').select('user_id').execute()
    users = [(u['user_id'],) for u in response.data]''',
    code
)

# Replace send_daily_summary
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("SELECT user_id FROM Users"\)\s*users = cursor\.fetchall\(\)',
    '''response = supabase.table('users').select('user_id').execute()
    users = [(u['user_id'],) for u in response.data]''',
    code
)
code = re.sub(
    r'cursor\.execute\("SELECT dhikr_id, title, daily_target FROM Dhikrs WHERE user_id=\?", \(user_id,\)\)\s*dhikrs = cursor\.fetchall\(\)',
    '''dhikrs_resp = supabase.table('dhikrs').select('id, title, daily_target').eq('user_id', user_id).execute()
        dhikrs = [(d['id'], d['title'], d['daily_target']) for d in dhikrs_resp.data]''',
    code
)
code = re.sub(
    r'cursor\.execute\("SELECT current_count FROM Daily_Progress WHERE user_id=\? AND dhikr_id=\? AND date=\?", \(user_id, dhikr_id, today\)\)\s*prog = cursor\.fetchone\(\)',
    '''prog_resp = supabase.table('daily_progress').select('current_count').eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
        prog = (prog_resp.data[0]['current_count'],) if prog_resp.data else None''',
    code
)
code = re.sub(
    r'conn\.close\(\)',
    '''pass''',
    code
)

# Replace start_action_handler
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("SELECT dhikr_id, title FROM Dhikrs WHERE user_id=\?", \(user_id,\)\)\s*dhikrs = cursor\.fetchall\(\)\s*pass',
    '''response = supabase.table('dhikrs').select('id, title').eq('user_id', user_id).execute()
        dhikrs = [(d['id'], d['title']) for d in response.data]''',
    code
)
# Remind yes handler
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("SELECT dhikr_id, title FROM Dhikrs WHERE user_id=\?", \(user_id,\)\)\s*dhikrs = cursor\.fetchall\(\)\s*pass',
    '''response = supabase.table('dhikrs').select('id, title').eq('user_id', user_id).execute()
    dhikrs = [(d['id'], d['title']) for d in response.data]''',
    code
)


# Replace settings_handler
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("SELECT full_name, age, habit_level FROM Users WHERE user_id=\?", \(callback\.from_user\.id,\)\)\s*user_data = cursor\.fetchone\(\)\s*pass',
    '''response = supabase.table('users').select('full_name, age, habit_level').eq('user_id', callback.from_user.id).execute()
    if response.data:
        ud = response.data[0]
        user_data = (ud['full_name'], ud['age'], ud['habit_level'])
    else:
        user_data = None''',
    code
)

# Replace process_settings_name
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("UPDATE Users SET full_name=\? WHERE user_id=\?", \(new_name, message\.from_user\.id\)\)\s*conn\.commit\(\)\s*pass',
    '''supabase.table('users').update({'full_name': new_name}).eq('user_id', message.from_user.id).execute()''',
    code
)

# Replace process_settings_habit
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("UPDATE Users SET habit_level=\? WHERE user_id=\?", \(new_habit, callback\.from_user\.id\)\)\s*conn\.commit\(\)\s*pass',
    '''supabase.table('users').update({'habit_level': new_habit}).eq('user_id', callback.from_user.id).execute()''',
    code
)

# Replace settings_reset_confirm_handler
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("DELETE FROM Daily_Progress WHERE user_id=\?", \(user_id,\)\)\s*cursor\.execute\("DELETE FROM Dhikrs WHERE user_id=\?", \(user_id,\)\)\s*cursor\.execute\("DELETE FROM Users WHERE user_id=\?", \(user_id,\)\)\s*conn\.commit\(\)',
    '''supabase.table('daily_progress').delete().eq('user_id', user_id).execute()
    supabase.table('dhikrs').delete().eq('user_id', user_id).execute()
    supabase.table('users').delete().eq('user_id', user_id).execute()''',
    code
)

# log_add amount
code = re.sub(
    r'conn = sqlite3\.connect\(DB_PATH\)\s*cursor = conn\.cursor\(\)\s*cursor\.execute\("UPDATE Dhikrs SET global_progress = global_progress \+ \? WHERE dhikr_id=\?", \(amount, dhikr_id\)\)\s*cursor\.execute\("""\s*INSERT INTO Daily_Progress \(user_id, dhikr_id, date, current_count\)\s*VALUES \(\?, \?, \?, \?\)\s*ON CONFLICT\(user_id, dhikr_id, date\)\s*DO UPDATE SET current_count = current_count \+ \?\s*""", \(user_id, dhikr_id, today, amount, amount\)\)\s*conn\.commit\(\)\s*pass',
    '''dhikr_resp = supabase.table('dhikrs').select('global_progress').eq('id', dhikr_id).execute()
    new_global = dhikr_resp.data[0]['global_progress'] + amount
    supabase.table('dhikrs').update({'global_progress': new_global}).eq('id', dhikr_id).execute()
    
    prog_resp = supabase.table('daily_progress').select('current_count').eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    if prog_resp.data:
        new_daily = prog_resp.data[0]['current_count'] + amount
        supabase.table('daily_progress').update({'current_count': new_daily}).eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    else:
        supabase.table('daily_progress').insert({'user_id': user_id, 'dhikr_id': dhikr_id, 'date': today, 'current_count': amount}).execute()''',
    code
)

with open('bot/bot2.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Done!')
