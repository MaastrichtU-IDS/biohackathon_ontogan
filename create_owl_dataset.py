import click as ck
from pathlib import Path
import mowl
mowl.init_jvm('2g')

from mowl.owlapi import OWLAPIAdapter
from mowl.owlapi.adapter import IRI
import java

@ck.command()
@ck.option('--data-root', '-dr', default=Path('data/'), type=Path,
            help='Data folder with HPO and disease annotations')
def main(data_root):
    hpo_file = data_root / 'hp.owl'
    annotations_file = data_root / 'phenotype.hpoa'
    owlapi = OWLAPIAdapter()
    hpo = owlapi.owl_manager.loadOntologyFromOntologyDocument(
        java.io.File(str(hpo_file)))
    
    with open(annotations_file) as f:
        for line in f:
            if line[0] == '#':
                continue
            it = line.strip().split()
            if it[2] == 'NOT':
                continue
            dis_id = it[0].split(':')
            dis_iri = f'http://mowl.borg/{dis_id[0]}_{dis_id[1]}'
            hp_id = it[3]
            hp_iri = hp_id.replace('HP:', 'http://purl.obolibrary.org/obo/HP_')
            hp_cls = owlapi.create_class(hp_iri)
            dis_cls = owlapi.create_class(dis_iri)
            has_phenotype = owlapi.create_object_property(
                'http://purl.obolibrary.org/obo/RO_0002200')
            has_phenotype_some_hp = owlapi.create_object_some_values_from(
                has_phenotype, hp_cls)
            axiom = owlapi.create_subclass_of(
                dis_cls, has_phenotype_some_hp)
            owlapi.owl_manager.addAxiom(hpo, axiom)
        
    out_file = java.io.File(str(data_root / 'dataset.owl'))
    owlapi.owl_manager.saveOntology(hpo, IRI.create(f'file://{out_file.getAbsolutePath()}'))

if __name__ == '__main__':
    main()
