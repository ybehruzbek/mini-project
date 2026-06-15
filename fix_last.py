with open('bot/bot2.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_block = """      conn = sqlite3.connect(DB_PATH)
      cursor = conn.cursor()
      
      cursor.execute("UPDATE Dhikrs SET global_progress = global_progress + ? WHERE dhikr_id=?", (amount, dhikr_id))
      cursor.execute(\"\"\"
          INSERT INTO Daily_Progress (user_id, dhikr_id, date, current_count) 
          VALUES (?, ?, ?, ?)
          ON CONFLICT(user_id, dhikr_id, date) DO UPDATE SET current_count = current_count + ?
      \"\"\", (user_id, dhikr_id, today, amount, amount))
      conn.commit()
      
      cursor.execute("SELECT daily_target FROM Dhikrs WHERE dhikr_id=?", (dhikr_id,))
      daily_tgt = cursor.fetchone()[0]
      cursor.execute("SELECT current_count FROM Daily_Progress WHERE user_id=? AND dhikr_id=? AND date=?", (user_id, dhikr_id, today))
      daily_prog = cursor.fetchone()[0]
      pass"""

new_block = """      dhikr_resp = supabase.table('dhikrs').select('global_progress, daily_target').eq('id', dhikr_id).execute()
      new_global = dhikr_resp.data[0]['global_progress'] + amount
      daily_tgt = dhikr_resp.data[0]['daily_target']
      supabase.table('dhikrs').update({'global_progress': new_global}).eq('id', dhikr_id).execute()
      
      prog_resp = supabase.table('daily_progress').select('current_count').eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
      if prog_resp.data:
          new_daily = prog_resp.data[0]['current_count'] + amount
          supabase.table('daily_progress').update({'current_count': new_daily}).eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
          daily_prog = new_daily
      else:
          supabase.table('daily_progress').insert({'user_id': user_id, 'dhikr_id': dhikr_id, 'date': today, 'current_count': amount}).execute()
          daily_prog = amount"""

if old_block in code:
    code = code.replace(old_block, new_block)
    with open('bot/bot2.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Replaced perfectly!")
else:
    print("Old block not found!")
