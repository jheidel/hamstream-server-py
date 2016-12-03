
all: clean fix lint


clean:
	pyclean .

fix:
	yapf -i -r --style style.cfg .

lint:
	find -name "*.py" -not -path "./old/*" | xargs pylint -f colorized -r n; true


