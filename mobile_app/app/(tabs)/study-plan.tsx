import { StyleSheet, Text } from "react-native";

import { ScreenShell } from "@/components/ScreenShell";
import { SectionCard } from "@/components/SectionCard";
import { activeExam, getExamSnapshot } from "@/lib/study-data";
import { theme } from "@/theme";

export default function StudyPlanScreen() {
  const snapshot = getExamSnapshot(activeExam);
  const topics = snapshot.study_plan.topics.slice(0, 3);

  return (
    <ScreenShell
      eyebrow="Weekly Plan"
      title="Study Plan"
      description={`A structured ${activeExam} weekly plan with time estimates, topic ordering, and reasons each topic matters.`}
    >
      {topics.length ? (
        topics.map((topic) => (
          <SectionCard
            key={topic.priority}
            title={`Priority ${topic.priority}`}
            subtitle={`${topic.topic} • ${topic.estimated_minutes} minutes`}
          >
            <Text style={styles.copy}>Why it matters: {topic.why_it_matters}</Text>
          </SectionCard>
        ))
      ) : (
        <SectionCard title="Plan Seed" subtitle="No synced plan yet">
          <Text style={styles.copy}>Save activity in Streamlit and the mobile sync file will populate the next study plan automatically.</Text>
        </SectionCard>
      )}
      <SectionCard title="Recovery Block" subtitle="20 minutes">
        <Text style={styles.copy}>Use the final block for miss review and one short timed set instead of adding another long session.</Text>
      </SectionCard>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  copy: {
    color: theme.colors.text,
    fontSize: theme.type.body,
    lineHeight: 22
  }
});
