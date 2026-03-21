import { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

import { shadows, theme } from "@/theme";

type SectionCardProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

export function SectionCard({ title, subtitle, children }: SectionCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      <View style={styles.body}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.card,
    padding: theme.spacing.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    gap: theme.spacing.sm,
    ...shadows.card
  },
  title: {
    color: theme.colors.text,
    fontSize: theme.type.subtitle,
    fontWeight: "700"
  },
  subtitle: {
    color: theme.colors.textMuted,
    fontSize: theme.type.body,
    lineHeight: 22
  },
  body: {
    gap: theme.spacing.sm
  }
});
