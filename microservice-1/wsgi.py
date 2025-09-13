from app import create_app
app = create_app()

# Para desarrollo local con `python wsgi.py` si quieres:
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)