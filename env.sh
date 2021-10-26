DIR="./tvenv"
python --version
pip --version
if [ -d "$DIR" ]; then
    echo "${DIR} is ready to use."
    source ./${DIR}/Scripts/activate
    echo "the venv actived"
else
    echo "Create virtual environment ${DIR}"
    python -m venv ${DIR}
    source ./${DIR}/Scripts/activate
    ./${DIR}/scripts/python -m pip install --upgrade pip
    pip install -r requirements.txt
fi
