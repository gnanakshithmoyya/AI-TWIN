import { useMemo, useState, useEffect } from 'react';
import { Container, Theme } from './settings/types';
import { VitaTwinApp } from './components/generated/VitaTwinApp';
import { Login } from './components/Login';
import { getAccessToken } from './lib/token';

let theme: Theme = 'light';
// only use 'centered' container for standalone components, never for full page apps or websites.
let container: Container = 'none';

function App() {
  const [authed, setAuthed] = useState<boolean>(!!getAccessToken());

  function setTheme(theme: Theme) {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  setTheme(theme);

  useEffect(() => {
    setAuthed(!!getAccessToken());
  }, []);

  const generatedComponent = useMemo(() => {
    // THIS IS WHERE THE TOP LEVEL GENRATED COMPONENT WILL BE RETURNED!
    return <VitaTwinApp />;
  }, []);

  if (!authed) {
    return <Login onAuth={() => setAuthed(true)} />;
  }

  if (container === 'centered') {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center">
        {generatedComponent}
      </div>
    );
  } else {
    return generatedComponent;
  }
}

export default App;
