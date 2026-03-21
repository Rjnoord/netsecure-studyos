import { ReactNode } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

import { shadows, theme } from "@/theme";

type ScreenShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
};

export function ScreenShell({ eyebrow, title, description, children }: ScreenShellProps) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <LinearGradient colors={["#102033", "#0f766e"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <Text style={styles.eyebrow}>{eyebrow}</Text>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
      </LinearGradient>
      <View style={styles.body}>{children}</View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.colors.background
  },
  content: {
    padding: theme.spacing.lg,
    gap: theme.spacing.lg
  },
  hero: {
    borderRadius: theme.radius.card,
    padding: theme.spacing.xl,
    gap: theme.spacing.sm
  },
  eyebrow: {
    color: "rgba(255,255,255,0.72)",
    textTransform: "uppercase",
    letterSpacing: 1.4,
    fontSize: theme.type.eyebrow,
    fontWeight: "700"
  },
  title: {
    color: "#ffffff",
    fontSize: theme.type.title,
    fontWeight: "800"
  },
  description: {
    color: "rgba(255,255,255,0.84)",
    fontSize: theme.type.body,
    lineHeight: 22
  },
  body: {
    gap: theme.spacing.md
  }
});
