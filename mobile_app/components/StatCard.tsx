import { StyleSheet, Text, View } from "react-native";

import { theme } from "@/theme";

type StatCardProps = {
  label: string;
  value: string;
  detail: string;
};

export function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
      <Text style={styles.detail}>{detail}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minWidth: 150,
    backgroundColor: theme.colors.surfaceMuted,
    borderRadius: theme.radius.card,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    gap: theme.spacing.xs
  },
  label: {
    color: theme.colors.textMuted,
    textTransform: "uppercase",
    letterSpacing: 0.8,
    fontSize: theme.type.eyebrow,
    fontWeight: "700"
  },
  value: {
    color: theme.colors.text,
    fontSize: 30,
    fontWeight: "800"
  },
  detail: {
    color: theme.colors.accent,
    fontSize: 13,
    fontWeight: "600"
  }
});
