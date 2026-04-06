def postprocess_schema_enums(result, generator, request, public):
    if 'components' in result and 'schemas' in result['components']:
        schemas = result['components']['schemas']
        
        replacements = {
            'GraduacaoEnum': 'PolicialGraduacaoEnum',
            'Unidade553Enum': 'UnidadePMEnum',
            'Status6aeEnum': 'StatusCustodiaEnum',
            'StatusNaEpocaEnum': 'StatusCustodiaEnum',
            'UnidadeOrigemEnum': 'UnidadePMOrigemEnum',
        }
        
        new_schemas = {}
        for name, schema in schemas.items():
            new_name = replacements.get(name, name)
            new_schemas[new_name] = schema
            
        result['components']['schemas'] = new_schemas
        
        for path_item in result.get('paths', {}).values():
            for operation in path_item.values():
                if isinstance(operation, dict):
                    _update_refs_in_dict(operation, replacements)
    
    return result


def _update_refs_in_dict(obj, replacements):
    if isinstance(obj, dict):
        if '$ref' in obj:
            for old_name, new_name in replacements.items():
                if old_name in obj['$ref']:
                    obj['$ref'] = obj['$ref'].replace(old_name, new_name)
        for value in obj.values():
            _update_refs_in_dict(value, replacements)
    elif isinstance(obj, list):
        for item in obj:
            _update_refs_in_dict(item, replacements)
