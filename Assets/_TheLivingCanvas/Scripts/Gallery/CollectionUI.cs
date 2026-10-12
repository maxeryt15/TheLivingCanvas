using System.Collections.Generic;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Npcs;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Progression;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Gallery
{
    /// <summary>Panel de la colección: sets con recompensa arriba y luego una fila por cultivo y, detrás de cada uno, una por variante, y al final una por mutación. Lo no descubierto sale en silueta.</summary>
    public class CollectionUI : ModalPanel
    {
        [SerializeField] RectTransform rowContainer;
        [Tooltip("Fila desactivada que se clona por entrada (RawImage 'Icon', Text 'Name'; el botón 'Buy' solo se muestra en los sets completos, como Claim).")]
        [SerializeField] GameObject rowTemplate;
        [SerializeField] Text messageLabel;
        [SerializeField] Wallet wallet;
        [SerializeField] PigmentStock stock;
        [SerializeField] PaintBrushController brush;

        readonly List<GameObject> rows = new();
        ArtistLevel artistLevel;
        CropDefinition[] crops;
        CollectionSet[] sets;

        protected override void Awake()
        {
            base.Awake();
            rowTemplate.SetActive(false);
        }

        public void Open(ArtistLevel artistLevel, CropDefinition[] crops, CollectionSet[] sets)
        {
            if (!TryOpen()) return;
            this.artistLevel = artistLevel;
            this.crops = crops;
            this.sets = sets;
            Populate();
        }

        void Populate()
        {
            var (found, total) = CollectionBoard.Count(artistLevel, crops);
            messageLabel.text = $"{found} / {total} discovered";

            foreach (var row in rows)
                Destroy(row);
            rows.Clear();

            foreach (var set in sets)
                AddSetRow(set);

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

        void AddSetRow(CollectionSet set)
        {
            bool complete = set.IsComplete(artistLevel);
            bool claimed = artistLevel.IsClaimed(set);
            var status = claimed ? "Claimed" : $"Reward: {set.RewardText}";
            var row = AddRow(Texture2D.whiteTexture, complete ? new Color(0.85f, 0.68f, 0.25f) : Color.black,
                $"{set.DisplayName}  {set.CountDiscovered(artistLevel)} / {set.Total}\n<size=18>{status}</size>");

            var claim = row.transform.Find("Buy");
            claim.gameObject.SetActive(complete && !claimed);
            claim.GetComponentInChildren<Text>().text = "Claim";
            var button = claim.GetComponent<Button>();
            button.onClick.RemoveAllListeners();
            button.onClick.AddListener(() => Claim(set));
        }

        void Claim(CollectionSet set)
        {
            if (!set.IsComplete(artistLevel) || !artistLevel.Claim(set)) return;
            var reward = CommissionRewards.Pay(set.RewardCoins, set.RewardXp, set.RewardPigment, set.RewardPigmentAmount, wallet, artistLevel, stock, brush);
            Populate();
            messageLabel.text = reward;
        }

        GameObject AddRow(Texture icon, Color tint, string text)
        {
            var row = Instantiate(rowTemplate, rowContainer);
            row.SetActive(true);
            var image = row.transform.Find("Icon").GetComponent<RawImage>();
            image.texture = icon;
            image.color = tint;
            row.transform.Find("Name").GetComponent<Text>().text = text;
            row.transform.Find("Buy").gameObject.SetActive(false);
            rows.Add(row);
            return row;
        }
    }
}
