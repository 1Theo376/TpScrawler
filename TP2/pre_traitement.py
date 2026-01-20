import jsonlines
from urllib.parse import urlparse, parse_qs


def extract_information(file):
    """
    Extract product identifiers and variants from URLs in a JSONL file.

    Parameters
    ----------
    file : str
        Path to the input JSONL file containing crawled documents.

    Returns
    -------
    list of dict
        List of documents enriched with `id_product` and `variant` fields.
    """
    L=[]
    with jsonlines.open(file) as reader:
        for obj in reader:
            L.append(obj)
    
    for o in L:
        url = o.get("url", "")
        p = urlparse(url)
        # Product id
        parts = [x for x in p.path.split("/") if x]  # ex: ["product", "10"]
        id_product = "No id"
        if len(parts) >= 2 and parts[0] == "product":
            id_product = parts[1]
            if id_product.isdigit():
                id_product = int(id_product)
        
        #variant
        variant = "No variant"
        qs = parse_qs(p.query)
        if "variant" in qs and qs["variant"]:
            variant = qs["variant"][0]

        o["id_product"] = id_product
        o["variant"] = variant
    return L

def add_information(L):
    """
    Save enriched documents to a JSONL output file.

    Parameters
    ----------
    L : list of dict
        List of enriched documents to be written to the output file.
    """
    with jsonlines.open("/home/ensai/Documents/Indexation/TpScrawler/output/products_with_id.jsonl", mode='w') as writer:
        for o in L:
            writer.write(o)


if __name__ == "__main__":
    inp = "/home/ensai/Documents/Indexation/TpScrawler/TP2/input/products.jsonl"
    out = "/home/ensai/Documents/Indexation/TpScrawler/TP2/input/products_with_id.jsonl"

    L = extract_information(inp)

    with jsonlines.open(out, mode="w") as writer:
        for o in L:
            writer.write(o)