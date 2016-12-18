
all: clean fix lint


clean:
	pyclean .

fix:
	yapf -i --style style.cfg *.py

lint:
	find -name "*.py" -not -path "./old/*" | xargs pylint -f colorized -r n; true


