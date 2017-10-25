## Submitter

|             |                     |
| ----------- | ------------------- |
| **Name**    | {{data["name"]}}    |
| **Program** | {{data["program"]}} |

## Request

|                    |                         |
| ------------------ | ----------------------- |
| **Trait Name**         | {{data["trait-name"]}}  |
| **Class**             | {{data["trait-class"]}} |
| **Definition**         | {{data["trait-def"]}}   |
| **Measurement Method** | {{data["method"]}}      |
| **Measurement Type**   | {{data["trait-type"]}}  |
{% if data["trait-type"]=="Unit" %}
| **Measurement Unit**   | {{data["unit"]}}        |
{% else %}

#### Categories

| ID       | Description |
| -------- | ----------- |
{% for c in data["categories"] %}
| **{{c[0]}}** | {{c[1]}}    |
{% endfor %}
{% endif %}
