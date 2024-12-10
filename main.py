from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import logging
import os
import threading
import numpy as np
import matplotlib.pyplot as plt


# Инициализация Flask приложения
app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
	filename='responses.log', 
	level=logging.INFO, 
	format='%(asctime)s - %(message)s'
)
N_QUESTIONS = 104
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
		updated_data.to_excel("responses.xlsx", index=False)

@app.route('/')
def quiz():
	"""Возвращает HTML-страницу с вопросами и вариантами ответов."""
	with open("quest.txt",encoding='utf-8') as f:
		questions = [
			{
				'question': f"{x + 1}. {i.strip()}",
				'options': [-2, -1, 0, 1, 2]
			} for x, i in enumerate(f.readlines()[:N_QUESTIONS])
		]
	return render_template('quiz.html', questions=questions)

@app.route('/submit', methods=['POST'])
def submit():
	"""Обрабатывает ответы и метаданные, сохраняет их в Parquet и логирует."""
	# ~ try:
	data = request.json
	metadata = data.get('metadata', {})
	responses = data.get('responses', [])

	# Объединяем метаданные и ответы в одну строку
	row = {response['question']: response['answer'] for response in responses}
	row.update(metadata)
	row['timestamp'] = pd.Timestamp.now()

	df = pd.DataFrame([row])

	# Сохранение в Parquet
	# ~ save_to_parquet(df)
	print(df.T)
	columns = ["параноидальность", "эпилептоидность", "гипертимность", "истероидность", "шизоидность", "психастения", "сензитивность", "гипотим", "конформность", "неустойчивость", "астения", "лабильность", "циклоидность"]
	df_count = df.iloc[0, :N_QUESTIONS].astype(float)
	for i in range(len(columns)):
		print(df_count.iloc[i::len(columns)])
		df[columns[i]] = np.sum(df_count.iloc[i::len(columns)])
		
	name_ = df['metadata1'].values[0][:16]
	print(name_)
	plt.figure(figsize=(12, 6))
	plt.plot(columns, df[columns].values.reshape(-1), "*--")
	plt.ylim([-16, 16])
	plt.yticks(np.arange(-16, 17))
	plt.grid()
	plt.title(name_)
	plt.xticks(rotation=90)
	plt.savefig(f"static/{name_}.png", bbox_inches='tight')
	print(df[columns])
	
	# Логирование
	logging.info(f"Saved response: {row}")

	return jsonify({'status': 'success', "id": f"/static/{name_}.png"}), 200
	# ~ except Exception as e:
		# ~ logging.error(f"Error saving response: {e}")
		# ~ return jsonify({'status': 'error', 'message': str(e)}), 500
		

if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0", port="5000")
