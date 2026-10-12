using System.Collections.Generic;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using TheLivingCanvas.Progression;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Gallery
{
    /// <summary>Panel de la colección: una fila por cultivo y, detrás de cada uno, una por variante, y al final una por mutación. Lo no descubierto sale en silueta.</summary>
    public class CollectionUI : ModalPanel
    {
        [SerializeField] RectTransform rowContainer;
        [Tooltip("Fila desactivada que se clona por entrada (RawImage 'Icon', Text 'Name'; el botón 'Buy' se oculta).")]
        [SerializeField] GameObject rowTemplate;
        [SerializeField] Text messageLabel;

        readonly List<GameObject> rows = new();

        protected override void Awake()
        {
            base.Awake();
            rowTemplate.SetActive(false);
        }

        public void Open(ArtistLevel artistLevel, CropDefinition[] crops)
        {
            if (!TryOpen()) return;

            var (found, total) = CollectionBoard.Count(artistLevel, crops);
            messageLabel.text = $"{found} / {total} discovered";

            foreach (var row in rows)
                Destroy(row);
            rows.Clear();

            foreach (var crop in crops)
            {
                bool cropFound = artistLevel.IsDiscovered(crop);
                AddRow(crop.Icon, cropFound ? Color.white : Color.black,
                    cropFound ? $"{crop.DisplayName}\n<size=18>Discovered</size>" : "???\n<size=18>Not painted yet</size>");

                foreach (var variant in crop.Variants)
                {
                    if (artistLevel.IsDiscovered(crop, variant))
                        AddRow(crop.Icon, variant.pigment.Color, $"    {variant.displayName}\n    <size=18>{variant.rarity} variant</size>");
                    else
                        AddRow(crop.Icon, Color.black,
                            $"    ???\n    <size=18>{variant.rarity} variant of {(cropFound ? crop.DisplayName : "???")} — not painted yet</size>");
                }
            }

            foreach (var mutation in Mutations.All)
            {
                if (artistLevel.IsDiscovered(mutation))
                    AddRow(Texture2D.whiteTexture, Color.white, $"{mutation.Name()}\n<size=18>{mutation.Effect()}</size>");
                else
                    AddRow(Texture2D.whiteTexture, Color.black, "???\n<size=18>Mutation — not grown yet</size>");
            }
        }

        void AddRow(Texture icon, Color tint, string text)
        {
            var row = Instantiate(rowTemplate, rowContainer);
            row.SetActive(true);
            var image = row.transform.Find("Icon").GetComponent<RawImage>();
            image.texture = icon;
            image.color = tint;
            row.transform.Find("Name").GetComponent<Text>().text = text;
            row.transform.Find("Buy").gameObject.SetActive(false);
            rows.Add(row);
        }
    }
}
