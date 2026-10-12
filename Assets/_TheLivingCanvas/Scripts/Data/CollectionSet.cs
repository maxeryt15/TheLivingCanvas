using System;
using System.Collections.Generic;
using TheLivingCanvas.Progression;
using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Una pieza de un set: un cultivo, una variante suya (variantId) o una mutación.</summary>
    [Serializable]
    public class CollectionEntry
    {
        public CropDefinition crop;
        [Tooltip("Vacío = el cultivo en sí; si no, la variante con ese id.")]
        public string variantId;
        [Tooltip("Distinto de None = la entrada es esa mutación (ignora crop y variantId).")]
        public Mutation mutation;
    }

    /// <summary>Set de la colección: al descubrir todas sus piezas se reclama una recompensa.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Collection Set", fileName = "CollectionSet")]
    public class CollectionSet : ScriptableObject
    {
        [SerializeField] string id;
        [SerializeField] string displayName;
        [SerializeField] CollectionEntry[] entries;
        [SerializeField] int rewardCoins;
        [SerializeField] int rewardXp;
        [Tooltip("Pigmento de recompensa (opcional).")]
        [SerializeField] PigmentDefinition rewardPigment;
        [SerializeField] int rewardPigmentAmount;

        public string Id => id;
        public string DisplayName => displayName;
        public int Total => entries.Length;
        public int RewardCoins => rewardCoins;
        public int RewardXp => rewardXp;
        public PigmentDefinition RewardPigment => rewardPigment;
        public int RewardPigmentAmount => rewardPigmentAmount;

        /// <summary>Piezas ya descubiertas.</summary>
        public int CountDiscovered(ArtistLevel artistLevel)
        {
            int found = 0;
            foreach (var entry in entries)
                if (IsDiscovered(artistLevel, entry)) found++;
            return found;
        }

        public bool IsComplete(ArtistLevel artistLevel) => CountDiscovered(artistLevel) == Total;

        /// <summary>Resumen de la recompensa, ej. "100 coins · 60 XP · 30 Gold Leaf".</summary>
        public string RewardText
        {
            get
            {
                var parts = new List<string>();
                if (rewardCoins > 0) parts.Add($"{rewardCoins} coins");
                if (rewardXp > 0) parts.Add($"{rewardXp} XP");
                if (rewardPigment != null) parts.Add($"{rewardPigmentAmount} {rewardPigment.DisplayName}");
                return string.Join(" · ", parts);
            }
        }

        static bool IsDiscovered(ArtistLevel artistLevel, CollectionEntry entry)
        {
            if (entry.mutation != Mutation.None) return artistLevel.IsDiscovered(entry.mutation);
            if (string.IsNullOrEmpty(entry.variantId)) return artistLevel.IsDiscovered(entry.crop);
            var variant = Array.Find(entry.crop.Variants, v => v.id == entry.variantId);
            return variant != null && artistLevel.IsDiscovered(entry.crop, variant);
        }

#if UNITY_EDITOR
        /// <summary>Solo para generar los assets desde herramientas de editor.</summary>
        public void EditorSetup(string newId, string newDisplayName, CollectionEntry[] newEntries, int newRewardCoins, int newRewardXp,
            PigmentDefinition newRewardPigment = null, int newRewardPigmentAmount = 0)
        {
            id = newId;
            displayName = newDisplayName;
            entries = newEntries;
            rewardCoins = newRewardCoins;
            rewardXp = newRewardXp;
            rewardPigment = newRewardPigment;
            rewardPigmentAmount = newRewardPigmentAmount;
        }
#endif
    }
}
