# DATAS

The objective of the collection of theses data is to have a deeper understanding of the graph, and specifically, of the classes. Ultimately, theses data can be used to help the kgbot.


### NPCCLass 

SPARQL query
```(sparql)
PREFIX enpkg_module: <https://enpkg.commons-lab.org/module/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX enpkg: <https://enpkg.commons-lab.org/kg/>

SELECT DISTINCT ?subject
WHERE {
    ?subject a enpkg:NPCClass .
}

```

### ChemicalTaxonomy 

SPQRAL query
```(sparql)
PREFIX enpkg_module: <https://enpkg.commons-lab.org/module/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX enpkg: <https://enpkg.commons-lab.org/kg/>

SELECT DISTINCT ?subject
WHERE {
    ?subject a enpkg:ChemicalTaxonomy .
}
```

## NPCClass vs ChemicalTaxonomy nodes

NPCCLass is a subclass of ChemicalTaxonomy
- There are 678 entries that are common to both files.
- There are 0 entries that are unique to npcclass.csv.
- There are 83 entries that are unique to chemical_taxonomy.csv.

And here are examples of entries that are unique to the chemical_taxonomy file:
``````
    https://enpkg.commons-lab.org/kg/npc_Alkaloids
    https://enpkg.commons-lab.org/kg/npc_Ornithine_derivatives
    https://enpkg.commons-lab.org/kg/npc_Lysine_alkaloids
    https://enpkg.commons-lab.org/kg/npc_Terpenoids
    https://enpkg.commons-lab.org/kg/npc_Steroids
``````  

BUT 

it exist a relationship has_npc_class but no has_chemical_taxonomy. So the first one is better in use cases.


## ChEMBLTarget 

SPARQL query
```(sparql)
PREFIX enpkg_module: <https://enpkg.commons-lab.org/module/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX chmbl: <https://www.ebi.ac.uk/chembl/target_report_card/>
PREFIX enpkg: <https://enpkg.commons-lab.org/kg/>

SELECT DISTINCT ?subject
WHERE {
    ?subject a enpkg_module:ChEMBLTarget .
}
```

Only 3 targets : 
'Leishmania donovani', 'Trypanosoma cruzi', 'Trypanosoma brucei rhodesiense'


## Taxon, wikidata ID 

```(sparql)
PREFIX enpkg_module: <https://enpkg.commons-lab.org/module/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX chmbl: <https://www.ebi.ac.uk/chembl/target_report_card/>
PREFIX enpkg: <https://enpkg.commons-lab.org/kg/>

SELECT DISTINCT ?taxon ?id
WHERE {
    ?subject enpkg:submitted_taxon ?taxon .
    ?subject enpkg:has_wd_id ?id .
}

```