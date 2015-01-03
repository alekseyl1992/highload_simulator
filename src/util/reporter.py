import json


def save_report(results, minimum):
    with open("../reports/template.html", "r") as template:
        template_str = template.read()

        with open("../reports/output.html", "w") as output:
            output.write(template_str % (json.dumps(results), minimum[0], int(minimum[1])))