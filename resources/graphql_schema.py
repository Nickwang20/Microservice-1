import graphene

from dbconnector import get_db_conn

## use graphql to search book
class AvgscoreType(graphene.ObjectType):
    id = graphene.String()
    avgscore = graphene.Float()

class Query(graphene.ObjectType):
    avgscores = graphene.List(AvgscoreType, id=graphene.String())

    def resolve_avgscores(self, info, id=None):
        conn = get_db_conn()
        query = "SELECT * FROM avgscores"
        if id is not None:
            query += f" WHERE id = '{id}'"
        print("Parsed SQL from GraphQL: " + query)
        result = conn.execute(query).fetchdf()
        return [AvgscoreType(**row) for index, row in result.iterrows()]

schema = graphene.Schema(query=Query)
