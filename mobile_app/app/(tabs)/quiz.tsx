import { StyleSheet, Text, View } from "react-native";

import { ScreenShell } from "@/components/ScreenShell";
import { SectionCard } from "@/components/SectionCard";
import { StatCard } from "@/components/StatCard";
import { activeExam, getExamSnapshot } from "@/lib/study-data";
import { theme } from "@/theme";

export default function QuizScreen() {
  const snapshot = getExamSnapshot(activeExam);

  return (
    <ScreenShell
      eyebrow="Practice Builder"
      title="Quiz"
      description={`A focused quiz workflow for ${activeExam} with room for domain filters, timers, and quick review cards.`}
    >
      <View style={styles.statsRow}>
        <StatCard label="Mode" value="Practice" detail="Shared local study flow" />
        <StatCard label="Queue" value={`${snapshot.review_queue.length}`} detail="Topics currently due" />
      </View>
      <SectionCard title="Quiz Setup" subtitle="This now reflects the synced exam snapshot instead of static placeholder text.">
        <Text style={styles.item}>Selected exam: {activeExam}</Text>
        <Text style={styles.item}>Recommended next topic: {snapshot.recommended_next_topic.topic}</Text>
        <Text style={styles.item}>Timer: Optional, saved per session</Text>
      </SectionCard>
      <SectionCard title="Review Flow" subtitle="After submission, this area can hold answer review, explanations, and follow-up prompts.">
        <Text style={styles.item}>Show correct answer and explanation</Text>
        <Text style={styles.item}>Flag repeated misses for study-plan carryover</Text>
        <Text style={styles.item}>Persist progress locally before any backend sync exists</Text>
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
