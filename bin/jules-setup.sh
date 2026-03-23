#!bin/sh
python -m venv .venv
.venv/bin/pip install -e .[dev]

echo "/app/bin/mytilus" | sudo tee -a /etc/shells
sudo chsh -s "/app/bin/mytilus" jules
sudo su - jules -c "!echo Jules shell is now Mytilus"
