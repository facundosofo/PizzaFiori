type Props = {
  title: string;
};

export const ModuleCard = ({ title }: Props) => {
  return (
    <div className="module-card">
      <h2>{title}</h2>
    </div>
  );
};
