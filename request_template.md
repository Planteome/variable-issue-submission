## Submitter

|             |                     |
| ----------- | ------------------- |
| **Name**    | {{data["name"]}}    |
| **Program** | {{data["program"]}} |

## Request

|                        |                           |
| ---------------------- | ------------------------- |
| **Trait Name**         | {{data["trait-name"]}}    |
| **Definition**         | {{data["trait-def"]}}     |
| **Trait Class**        | {{data["trait-class"]}}   |
| **Measurement Method** | {{data["method"]}}        |
| **Measurement Type**   | {{data["variable-type"]}} |
{% if data["variable-type"]=="Unit" %}
| **Measurement Unit**   | {{data["unit"]}}           |
{% else %}

#### Categories

| ID       | Description |
| -------- | ----------- |
{% for c in data["categories"] %}
| **{{c[0]}}** | {{c[1]}}    |
{% endfor %}
{% endif %}
