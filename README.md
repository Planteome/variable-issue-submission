# variable-issue-submission
This repo contains python3 code and other required files for hosting a form & making API calls in order to create ontology variable requests. A log of all request is avaible (password protected) at `$ROOTURL/log`. In order to run, the script accesses files relative to itself and so should be launched with the repo as the working directory. It also requires a `config.json` file in the following format: 

```javascript
{
    "token":"GitHubTokenHere",
    "username":"log_username",
    "password":"log_password"
}
```
