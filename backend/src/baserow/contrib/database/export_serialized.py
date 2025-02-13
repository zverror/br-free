class DatabaseExportSerializedStructure:
    @staticmethod
    def database(tables):
        return {"tables": tables}

    @staticmethod
    def table(id, name, order, fields, views, rows, data_sync):
        return {
            "id": id,
            "name": name,
            "order": order,
            "fields": fields,
            "views": views,
            "rows": rows,
            "data_sync": data_sync,
        }

    @staticmethod
    def row(id, order, created_on, updated_on, created_by=None, last_modified_by=None):
        optional = {}

        if created_by:
            optional["created_by"] = created_by.email

        if last_modified_by:
            optional["last_modified_by"] = last_modified_by.email

        return {
            "id": id,
            "order": order,
            "created_on": created_on,
            "updated_on": updated_on,
            **optional,
        }

    @staticmethod
    def file_field_value(name, visible_name, original_name):
        return {
            "name": name,
            "visible_name": visible_name,
            "original_name": original_name,
        }
