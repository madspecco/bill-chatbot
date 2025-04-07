bill_extraction_schema = {
    "name": "extract_bill_items",
    "description": "Extracts structured components from an energy bill",
    "parameters": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "quantity": {"type": "string"},
                        "unit_price": {"type": "string"},
                        "total": {"type": "string"}
                    },
                    "required": ["label", "total"]
                }
            }
        },
        "required": ["items"]
    }
}
