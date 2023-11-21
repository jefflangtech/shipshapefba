import json

def load_config():
  with open('app/config.json', 'r') as file:
    config = json.load(file)
  return config


if __name__ == '__main__':
  config = load_config()

  print(f"Database path: {config['database']['path']}")