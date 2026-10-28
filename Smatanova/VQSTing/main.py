from website import create_app

app = create_app()
app.config['TEMPLATES_AUTO_RELOAD'] = True   # template tweaks without a restart

if __name__ == '__main__':
    app.run(debug=False)