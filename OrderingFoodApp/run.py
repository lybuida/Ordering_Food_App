#run.py
from OrderingFoodApp import init_app

app = init_app()

if __name__ == '__main__':
    from OrderingFoodApp.routes.admin import *

    app.run(debug=True)