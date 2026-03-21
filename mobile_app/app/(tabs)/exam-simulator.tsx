import { StyleSheet, Text, View } from "react-native";

import { ScreenShell } from "@/components/ScreenShell";
import { SectionCard } from "@/components/SectionCard";
import { StatCard } from "@/components/StatCard";
import { activeExam, getExamSnapshot } from "@/lib/study-data";
import { theme } from "@/theme";

export default function ExamSimulatorScreen() {
  const snapshot = getExamSnapshot(activeExam);

  return (
    <ScreenShell
      eyebrow="Long Form"
      title="Exam Simulator"
      description={`A scaffold for timed ${activeExam} simulator runs, fatigue mode, and block-by-block pacing feedback.`}
    >
      <View style={styles.statsRow}>
        <StatCard label="Simulator" value="100 Q" detail="Fatigue mode ready" />
        <StatCard label="Prediction" value={`${snapshot.prediction.range_low}-${snapshot.prediction.range_high}%`} detail="Shared local estimate" />
      </View>
      <SectionCard title="Fatigue Simulation" subtitle="This card can evolve into a persistent endurance tracker once data sync is added.">
        <Text style={styles.item}>Late-session accuracy graph placeholder</Text>
        <Text style={styles.item}>Progress checkpoint at 25-question intervals</Text>
        <Text style={styles.item}>Post-exam recovery plan summary</Text>
      </SectionCard>
      <SectionCard title="Domain Breakdown" subtitle="A future screen state can render domain confidence after the exam completes.">
        {snapshot.confidence_by_domain.length ? (
          snapshot.confidence_by_domain.slice(0, 3).map((row) => (
            <Text style={styles.item} key={row.domain}>
              {row.domain}: {row.confidence_pct}%
            </Text>
          ))
        ) : (
          <Text style={styles.item}>No domain-confidence history yet. Save simulator results in Streamlit to populate this view.</Text>
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
  item: {
    color: theme.colors.text,
    fontSize: theme.type.body,
    lineHeight: 22
  }
});
