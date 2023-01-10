#!/usr/bin/env python3
"""
Entry point for our API. Exists solely to launch our flask app.
"""
from grubstack import app
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8082)
