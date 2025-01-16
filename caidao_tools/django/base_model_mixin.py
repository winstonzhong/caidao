
class ModelMixin:

    @classmethod
    def get_records(cls, query_data=None, offset=0, limit=10):

        query_data = dict() if query_data is None else query_data

        if offset:
            query_data['id__gt'] = offset
        print('query_data', query_data)
        q = cls.objects.filter(**query_data)
        if limit:
            records = q[:limit]
        return records

    @classmethod
    def get_data_list(cls, query_data=None, offset=0, limit=10, value_list=None):

        value_list = list() if value_list is None else value_list
        data_list = cls.get_records(query_data=query_data, offset=offset, limit=limit).values(*value_list)
        return list(data_list)
