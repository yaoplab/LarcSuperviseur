# Reflow de la grille de cartes

## Problème

Les cartes élèves (144×233 px) doivent s'adapter à la largeur de la fenêtre.

## Algorithme

```python
def reflow(self):
    avail_w = self._scroll.viewport().width()   # largeur dispo
    cfg = DEFAULT_CONFIG                         # CardConfig(144, 233)
    card_w = cfg.card_w                          # 144
    spacing = cfg.spacing                        # 8
    cols = max(1, (avail_w + spacing) // (card_w + spacing))
    
    # Extraire les StudentCard du layout
    cards = []
    for i in reversed(range(layout.count())):
        w = layout.itemAt(i).widget()
        if isinstance(w, StudentCard):
            cards.insert(0, w)
        else:
            w.deleteLater()  # spacers
    
    # Re-placer dans la grille
    for idx, card in enumerate(cards):
        layout.addWidget(card, idx // cols, idx % cols, Qt.AlignCenter)
    
    # Compléter la dernière ligne avec des spacers invisibles
    remaining = len(cards) % cols
    if remaining:
        for i in range(cols - remaining):
            spacer = QWidget()
            spacer.setFixedSize(cfg.card_w, cfg.card_h)
            layout.addWidget(spacer, len(cards)//cols, cols-remaining+i, Qt.AlignCenter)
```

## Déclencheur

`MainWindow.resizeEvent()` → `ClassPanel.reflow()` si mode classe actif.
