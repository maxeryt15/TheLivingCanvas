using System;
using System.Collections.Generic;
using TheLivingCanvas.Data;
using TheLivingCanvas.Save;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Pigmento que tiene el jugador, en unidades por color. Se gasta al terminar una pintura según el área
    /// pintada (ver <see cref="PaintUsage"/>). Sin límite de almacenamiento por ahora.
    /// </summary>
    [DefaultExecutionOrder(-100)] // las cantidades iniciales están antes de que la paleta las lea
    public class PigmentStock : MonoBehaviour, ISaveable
    {
        [Serializable]
        struct StartingAmount
        {
            public PigmentDefinition pigment;
            public int amount;
        }

        [SerializeField] StartingAmount[] startingAmounts = Array.Empty<StartingAmount>();

        readonly Dictionary<PigmentDefinition, int> amounts = new();

        /// <summary>Cualquier cambio en las cantidades.</summary>
        public event Action Changed;

        void Awake()
        {
            foreach (var start in startingAmounts)
                if (start.pigment != null)
                    amounts[start.pigment] = start.amount;
        }

        public int Get(PigmentDefinition pigment) => amounts.TryGetValue(pigment, out int amount) ? amount : 0;

        public void Add(PigmentDefinition pigment, int amount)
        {
            if (pigment == null || amount <= 0) return;
            amounts[pigment] = Get(pigment) + amount;
            Changed?.Invoke();
        }

        /// <summary>Primer pigmento que no alcanza para <paramref name="cost"/>, o null si alcanza todo.</summary>
        public PigmentDefinition FindShortage(IReadOnlyDictionary<PigmentDefinition, int> cost)
        {
            foreach (var pair in cost)
                if (Get(pair.Key) < pair.Value)
                    return pair.Key;
            return null;
        }

        /// <summary>Gasta todo <paramref name="cost"/> a la vez; false (sin gastar nada) si falta algo.</summary>
        public bool TrySpend(IReadOnlyDictionary<PigmentDefinition, int> cost)
        {
            if (FindShortage(cost) != null) return false;
            foreach (var pair in cost)
                amounts[pair.Key] = Get(pair.Key) - pair.Value;
            Changed?.Invoke();
            return true;
        }

        public void WriteSave(SaveData data)
        {
            data.pigments.Clear();
            foreach (var pair in amounts)
                data.pigments.Add(new AmountEntry { id = pair.Key.Id, amount = pair.Value });
        }

        /// <summary>Las cantidades guardadas sustituyen a las iniciales.</summary>
        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            amounts.Clear();
            foreach (var entry in data.pigments)
                if (registry.FindPigment(entry.id) is { } pigment)
                    amounts[pigment] = Mathf.Max(0, entry.amount);
            Changed?.Invoke();
        }

#if UNITY_EDITOR
        public void EditorSetStartingAmounts(PigmentDefinition[] pigments, int[] values)
        {
            startingAmounts = new StartingAmount[pigments.Length];
            for (int i = 0; i < pigments.Length; i++)
                startingAmounts[i] = new StartingAmount { pigment = pigments[i], amount = values[i] };
        }
#endif
    }
}
