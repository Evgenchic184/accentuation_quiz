from flask import Flask, render_template, request, jsonify
import pandas as pd
import logging
import os
import threading

# Инициализация Flask приложения
app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
	filename='responses.log', 
	level=logging.INFO, 
	format='%(asctime)s - %(message)s'
)

# Имя файла для хранения данных в Parquet
parquet_file = 'responses.parquet'
lock = threading.Lock()

def save_to_parquet(data):
	"""Сохраняет данные в Parquet-файл с учетом параллельной записи."""
	with lock:
		if os.path.exists(parquet_file):
			existing_data = pd.read_parquet(parquet_file)
			updated_data = pd.concat([existing_data, data], ignore_index=True)
		else:
			updated_data = data
		updated_data.to_parquet(parquet_file, index=False)

@app.route('/')
def quiz():
	"""Возвращает HTML-страницу с вопросами и вариантами ответов."""
	with open("quest.txt",encoding='utf-8') as f:
		questions = [
			{
				'question': i.strip(),
				'options': [-2, -1, 0, 1, 2]
			} for i in f.readlines()
		]
	return render_template('quiz.html', questions=questions)

@app.route('/submit', methods=['POST'])
def submit():
	"""Обрабатывает ответы и метаданные, сохраняет их в Parquet и логирует."""
	try:
		data = request.json
		metadata = data.get('metadata', {})
		responses = data.get('responses', [])

		# Объединяем метаданные и ответы в одну строку
		row = {response['question']: response['answer'] for response in responses}
		row.update(metadata)
		row['timestamp'] = pd.Timestamp.now()

		df = pd.DataFrame([row])

		# Сохранение в Parquet
		save_to_parquet(df)

		# Логирование
		logging.info(f"Saved response: {row}")

		return jsonify({'status': 'success'}), 200
	except Exception as e:
		logging.error(f"Error saving response: {e}")
		return jsonify({'status': 'error', 'message': str(e)}), 500
		

if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0", port="5000")
