"""Terminal et Streamlit utilisent désormais exactement le même pipeline."""
from app.conversation import profil_vide
from app.pipeline import traiter

def main():
    profil=profil_vide()
    question=None
    print("Assistant finance — écrire quitter pour terminer, nouveau pour réinitialiser.")
    while True:
        try:
            message=input("Vous : ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if message.lower()=='quitter': break
        if message.lower()=='nouveau':
            profil,question=profil_vide(),None
            continue
        r=traiter(message,profil,question)
        profil,question=r.profil,r.derniere_question
        print(r.texte)
        if r.dossier: print(r.dossier)

if __name__=='__main__': main()
