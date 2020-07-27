import React, { useEffect, useState } from 'react';

import { ApolloClient, ApolloProvider, InMemoryCache, useQuery } from '@apollo/client';
import { loader } from 'graphql.macro';


import Checkbox from '@material-ui/core/Checkbox';
import Grid from '@material-ui/core/Grid';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import Skeleton from '@material-ui/lab/Skeleton';

import DelayedRender from './DelayedRender';


const client = new ApolloClient({
    uri: 'http://localhost:8000/graphql/',
    cache: new InMemoryCache(),
});


const GetProcessApplicationsQuery = loader('./GetProcessApplications.graphql');


function Menu({ selection, setSelection }) {

    return (
        <List component="nav" aria-label="main mailbox folders">
          {selection === undefined ? [1, 2, 3].map((key) => (
              <DelayedRender>
                <ListItem key={key}>
                  <ListItemIcon>
                    <Skeleton variant="rect" width={16}/>
                  </ListItemIcon>
                  <ListItemText primary={<Skeleton />} />
                </ListItem>
              </DelayedRender>
          )) : selection.map(([key, selected], i) => (
              <ListItem
                key={`${i}-${key}`}
                button
                selected={selected}
                onClick={() => setSelection(
                    selection.map(([k, s]) => [k, k === key ? !selected : s])
                )}
              >
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={selected}
                    tabIndex={-1}
                    disableRipple
                    inputProps={{ 'aria-labelledby': `menu-label-${i}-${key}` }}
                  />
                </ListItemIcon>
                <ListItemText id={`menu-label-${i}-${key}`} primary={key} />
              </ListItem>
          ))}
        </List>
    );
}

function Notifications({ processApplications }) {
    return (
        <span>Hello!</span>
    );
}

function App() {
    const [selection, setSelection] = useState(undefined);

    const { loading, data, error } = useQuery(GetProcessApplicationsQuery, {
        onCompleted({ processApplications }) {
            setSelection(processApplications.map(({ name }) => [name, false]));
        },
    });

    console.log({
        loading,
        error,
        data,
        GetProcessApplicationsQuery,
    });

    return (
        <Grid container>
          <Grid item xs={3}>
            <Menu selection={selection} setSelection={setSelection} />
          </Grid>
          <Grid item xs>
            <Notifications processApplications={data} />
          </Grid>

        </Grid>
    );
}

function AppWithProviders() {
    return (
        <ApolloProvider client={client}>
          <App />
        </ApolloProvider>
    );
}

export default AppWithProviders;
