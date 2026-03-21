import { StyleSheet, Text, View } from "react-native";

import { ScreenShell } from "@/components/ScreenShell";
import { SectionCard } from "@/components/SectionCard";
import { StatCard } from "@/components/StatCard";
import { activeExam, getExamSnapshot } from "@/lib/study-data";
import { theme } from "@/theme";

export default function DashboardScreen() {
  const snapshot = getExamSnapshot(activeExam);
  const confidenceRows = snapshot.confidence_by_domain.slice(0, 3);

  return (
    <ScreenShell
      eyebrow="NetSecure StudyOS"
      title="Dashboard"
      description={`A mobile-first command center for ${activeExam} readiness, weak-topic pressure, and local study momentum.`}
    >
      <View style={styles.statsRow}>
        <StatCard label="Readiness" value={`${snapshot.readiness}`} detail="Smoothed confidence score" />
        <StatCard label="Latest" value={`${snapshot.latest_score}%`} detail="Most recent saved attempt" />
      </View>
      <SectionCard title="Recommended Next Topic" subtitle="Mirrored from the shared local sync snapshot.">
        <Text style={styles.body}>{snapshot.recommended_next_topic.topic}</Text>
        <Text style={styles.caption}>{snapshot.recommended_next_topic.reason}</Text>
      </SectionCard>
      <SectionCard title="Confidence By Domain" subtitle="The app reads the same local sync file that Streamlit updates.">
        {confidenceRows.length ? (
          confidenceRows.map((row) => (
            <View style={styles.domainRow} key={row.domain}>
              <Text style={styles.domain}>{row.domain}</Text>
              <Text style={styles.value}>{row.confidence_pct}%</Text>
            </View>
          ))
        ) : (
          <Text style={styles.caption}>No confidence data yet. Save a few quizzes in Streamlit to populate this screen.</Text>
        )}
      </SectionCard>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  statsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: theme.spacing.md
  },
  body: {
    color: theme.colors.text,
    fontSize: theme.type.body,
    lineHeight: 22
  },
  caption: {
    color: theme.colors.textMuted,
    fontSize: 13
  },
  domainRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: theme.spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border
  },
  domain: {
    color: theme.colors.text,
    fontSize: theme.type.body,
    fontWeight: "600"
  },
  value: {
    color: theme.colors.accent,
    fontSize: 16,
    fontWeight: "700"
  }
});
