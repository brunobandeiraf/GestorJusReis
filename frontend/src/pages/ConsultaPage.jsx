import ConsultaAvulsa from '../components/ConsultaAvulsa/index';

function ConsultaPage() {
  return (
    <div style={styles.container}>
      <ConsultaAvulsa />
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '1rem',
  },
};

export default ConsultaPage;
