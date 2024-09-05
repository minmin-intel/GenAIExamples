from langchain_community.utilities import SQLDatabase

path = "/localdisk/minminho/TAG-Bench/dev_folder/dev_databases/california_schools/california_schools.sqlite"
uri= "sqlite:///{path}".format(path=path)
db = SQLDatabase.from_uri(uri)
print(db.dialect)
print(db.get_usable_table_names())
print(db.get_table_info_no_throw())
# print(db.run("SELECT * FROM schools LIMIT 3;"))

