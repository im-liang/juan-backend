# juan backend

pip freeze > requirements.txt

Create a new virtual environment for your project:
pipx install virtualenv

Navigate to your project directory and create a virtual environment:
python3 -m venv venv

Activate the virtual environment:
source venv/bin/activate


export ACCOUNT_URI=$(az cosmosdb show --resource-group juan --name generald2b --query documentEndpoint --output tsv)
export ACCOUNT_KEY=$(az cosmosdb keys list --resource-group juan --name generald2b --query primaryMasterKey --output tsv)

dependency:
flask
flask-jwt-extended
azure-cosmos
google-auth
azure-identity
aiohttp